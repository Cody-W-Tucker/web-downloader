{
  description = "A web downloader utility in Python";

  inputs.nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/0.1";

  outputs =
    { self, nixpkgs, ... }:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      forEachSupportedSystem =
        f:
        nixpkgs.lib.genAttrs supportedSystems (
          system:
          f {
            inherit system;
            pkgs = import nixpkgs { inherit system; };
          }
        );

      pythonVersion = "3.13";

      concatMajorMinor =
        lib: v:
        lib.pipe v [
          lib.versions.splitVersion
          (lib.sublist 0 2)
          lib.concatStrings
        ];

      pythonPackages =
        ps: with ps; [
          requests
          lxml
          tqdm
          python-dotenv
          fake-useragent
          pyyaml
          beautifulsoup4
          pytest
        ];

      mkSystem =
        { pkgs, system }:
        let
          src = ./.;
          python = pkgs."python${concatMajorMinor pkgs.lib pythonVersion}";
          pythonWithPackages = python.withPackages pythonPackages;

          npmDeps = pkgs.fetchNpmDeps {
            inherit src;
            hash = "sha256-dVnAPkhcROX1YaEsOwVa+W2PIqfcet8BG7mpyfrQqY4=";
          };

          nodeModules = pkgs.stdenvNoCC.mkDerivation {
            pname = "web-downloader-node-modules";
            version = "0.1.0";

            inherit src npmDeps;

            nativeBuildInputs = [
              pkgs.nodejs_22
              pkgs.npmHooks.npmConfigHook
            ];

            npmInstallFlags = [ "--omit=dev" ];
            dontBuild = true;

            installPhase = ''
              mkdir -p $out/lib/node_modules
              cp -r node_modules/. $out/lib/node_modules/
            '';
          };

          package = pkgs.stdenv.mkDerivation {
            pname = "web-downloader";
            version = "0.1.0";

            inherit src;

            nativeBuildInputs = [ pkgs.pkg-config ];

            buildInputs = [
              pythonWithPackages
              pkgs.libxml2
              pkgs.libxslt
              pkgs.zlib
            ];

            nativeCheckInputs = [
              pkgs.nodejs_22
              pythonWithPackages
            ];

            dontBuild = true;
            doCheck = true;

            checkPhase = ''
              export DEFUDDLE_WRAPPER="$PWD/src/defuddle_wrapper.js"
              export DEFUDDLE_NODE_MODULES="${nodeModules}/lib/node_modules"
              export NIX_NODE_PATH="${pkgs.nodejs_22}/bin/node"
              export PYTHONPATH="$PWD/src''${PYTHONPATH:+:$PYTHONPATH}"

              pytest
            '';

            installPhase = ''
              mkdir -p $out/bin
              mkdir -p $out/lib/web-downloader

              cp -r $src/src/. $out/lib/web-downloader/

              cat > $out/bin/web-downloader <<'WRAPPER'
#!/bin/sh

export DEFUDDLE_WRAPPER="@out@/lib/web-downloader/defuddle_wrapper.js"
export DEFUDDLE_NODE_MODULES="@nodeModules@/lib/node_modules"
export NIX_NODE_PATH="@node@/bin/node"
export NODE_PATH="@nodeModules@/lib/node_modules''${NODE_PATH:+:$NODE_PATH}"
export PYTHONPATH="@out@/lib/web-downloader''${PYTHONPATH:+:$PYTHONPATH}"

if [ $# -lt 1 ]; then
  echo "Usage: web-downloader URL [options]"
  exit 1
fi

URL="$1"
shift

case "$URL" in
  --help|-h|-*)
    exec @python@/bin/python @out@/lib/web-downloader/main.py "$URL" "$@"
    ;;
esac

HAS_CUSTOM_OUTPUT=0
PREV_ARG=""

for arg in "$@"; do
  if [ "$PREV_ARG" = "--output-dir" ]; then
    HAS_CUSTOM_OUTPUT=1
    break
  fi
  PREV_ARG="$arg"
done

if [ "$HAS_CUSTOM_OUTPUT" -eq 0 ]; then
  DOMAIN=$(
    @python@/bin/python - "$URL" <<'PY'
from urllib.parse import urlparse
import sys

host = urlparse(sys.argv[1]).hostname or ""
print(host.removeprefix("www."))
PY
  )

  exec @python@/bin/python @out@/lib/web-downloader/main.py "$URL" --output-dir "./$DOMAIN" "$@"
fi

exec @python@/bin/python @out@/lib/web-downloader/main.py "$URL" "$@"
WRAPPER

              substituteInPlace $out/bin/web-downloader \
                --subst-var out \
                --subst-var-by python ${pythonWithPackages} \
                --subst-var-by node ${pkgs.nodejs_22} \
                --subst-var-by nodeModules ${nodeModules}

              chmod +x $out/bin/web-downloader

              cat > $out/bin/defuddle <<'DEFUDDLE'
#!/bin/sh

exec @node@/bin/node @nodeModules@/lib/node_modules/defuddle/dist/cli.js "$@"
DEFUDDLE

              substituteInPlace $out/bin/defuddle \
                --subst-var-by node ${pkgs.nodejs_22} \
                --subst-var-by nodeModules ${nodeModules}

              chmod +x $out/bin/defuddle
            '';

            meta.mainProgram = "web-downloader";
          };

          devCommand = pkgs.writeShellScriptBin "web-downloader" ''
            export DEFUDDLE_WRAPPER="$WEB_DOWNLOADER_ROOT/src/defuddle_wrapper.js"
            export DEFUDDLE_NODE_MODULES="${nodeModules}/lib/node_modules"
            export NIX_NODE_PATH="${pkgs.nodejs_22}/bin/node"
            export NODE_PATH="${nodeModules}/lib/node_modules''${NODE_PATH:+:$NODE_PATH}"
            export PYTHONPATH="$WEB_DOWNLOADER_ROOT/src''${PYTHONPATH:+:$PYTHONPATH}"

            exec ${pythonWithPackages}/bin/python "$WEB_DOWNLOADER_ROOT/src/main.py" "$@"
          '';

          defuddleDevCommand = pkgs.writeShellScriptBin "defuddle" ''
            export NODE_PATH="${nodeModules}/lib/node_modules''${NODE_PATH:+:$NODE_PATH}"

            exec ${pkgs.nodejs_22}/bin/node "${nodeModules}/lib/node_modules/defuddle/dist/cli.js" "$@"
          '';
        in
        {
          packages.default = package;

          devShells.default = pkgs.mkShell {
            packages = [
              pythonWithPackages
              pkgs.nodejs_22
              pkgs.libxml2
              pkgs.libxslt
              pkgs.zlib
              pkgs.pkg-config
              devCommand
              defuddleDevCommand
            ];

            shellHook = ''
              export WEB_DOWNLOADER_ROOT=$(pwd)
              export DEFUDDLE_WRAPPER="$WEB_DOWNLOADER_ROOT/src/defuddle_wrapper.js"
              export DEFUDDLE_NODE_MODULES="${nodeModules}/lib/node_modules"
              export NIX_NODE_PATH="${pkgs.nodejs_22}/bin/node"
              export NODE_PATH="${nodeModules}/lib/node_modules''${NODE_PATH:+:$NODE_PATH}"
              export PYTHONPATH="$WEB_DOWNLOADER_ROOT/src''${PYTHONPATH:+:$PYTHONPATH}"

              echo "Web downloader development environment ready!"
              echo "Run: web-downloader <url>"
            '';
          };
        };
    in
    {
      packages = forEachSupportedSystem ({ pkgs, system }: (mkSystem { inherit pkgs system; }).packages);

      nixosModules.default = import ./nixos-module.nix;

      nixosModule = self.nixosModules.default;

      devShells = forEachSupportedSystem ({ pkgs, system }: (mkSystem { inherit pkgs system; }).devShells);
    };
}
