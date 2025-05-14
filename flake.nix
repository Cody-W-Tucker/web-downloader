{
  description = "A web downloader utility in Python";

  inputs.nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/0.1";

  outputs = { self, nixpkgs, ... }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });

      pythonVersion = "3.13";
    in
    {
      packages = forEachSupportedSystem ({ pkgs }:
        let
          concatMajorMinor = v:
            pkgs.lib.pipe v [
              pkgs.lib.versions.splitVersion
              (pkgs.lib.sublist 0 2)
              pkgs.lib.concatStrings
            ];

          python = pkgs."python${concatMajorMinor pythonVersion}";
          
          pythonWithPackages = python.withPackages (ps: with ps; [
            beautifulsoup4
            requests
            lxml
            markdownify
            tqdm
            python-dotenv
            fake-useragent
            pyyaml
          ]);
        in
        {
          default = pkgs.stdenv.mkDerivation {
            pname = "web-downloader";
            version = "0.1.0";
            src = ./.;
            
            buildInputs = [
              pythonWithPackages
              pkgs.libxml2
              pkgs.libxslt
              pkgs.zlib
            ];
            
            nativeBuildInputs = [
              pkgs.pkg-config
            ];
            
            installPhase = ''
              mkdir -p $out/bin
              mkdir -p $out/lib
              
              # Create proper Python package structure
              mkdir -p $out/lib/web-downloader
              cp -r ./src/* $out/lib/web-downloader/
              touch $out/lib/web-downloader/__init__.py
              
              # Make sure all modules can be imported
              for file in $out/lib/web-downloader/*.py; do
                # We can't use dots in Python module names, so direct execution is better
                sed -i 's/from \./from /' $file || true
              done
              
              # Create the domain-folder wrapper as the primary executable
              cat > $out/bin/web-downloader << EOF
              #!/bin/sh
              # Set up Python path to find our modules
              export PYTHONPATH="$out/lib:$PYTHONPATH"
              
              # Extract domain and use it as output directory
              if [ \$# -lt 1 ]; then
                echo "Usage: web-downloader URL [options]"
                exit 1
              fi
              
              URL="\$1"
              shift
              
              # Special case for --help and other flags
              if [ "\$URL" = "--help" ] || [ "\$URL" = "-h" ] || [[ "\$URL" == -* ]]; then
                exec ${pythonWithPackages}/bin/python $out/lib/web-downloader/main.py "\$URL" "\$@"
                exit 0
              fi
              
              # Extract domain from URL
              DOMAIN=\$(echo "\$URL" | sed -E 's|^https?://([^/]+).*|\1|' | sed 's/^www\.//')
              
              # Check if user specified an output directory
              HAS_CUSTOM_OUTPUT=false
              NEXT_IS_OUTPUT=false
              
              for arg in "\$@"; do
                if [ "\$NEXT_IS_OUTPUT" = "true" ]; then
                  OUTPUT_DIR="\$arg"
                  HAS_CUSTOM_OUTPUT=true
                  NEXT_IS_OUTPUT=false
                elif [ "\$arg" = "--output-dir" ]; then
                  NEXT_IS_OUTPUT=true
                fi
              done
              
              # Only add our domain-based folder if user didn't specify one
              if [ "\$HAS_CUSTOM_OUTPUT" = "false" ]; then
                exec ${pythonWithPackages}/bin/python $out/lib/web-downloader/main.py "\$URL" --output-dir "./\$DOMAIN" "\$@"
              else
                # User specified output-dir, respect it
                exec ${pythonWithPackages}/bin/python $out/lib/web-downloader/main.py "\$URL" "\$@"
              fi
              EOF
              
              chmod +x $out/bin/web-downloader
            '';
          };
        });

      nixosModules.default = import ./nixos-module.nix;
      
      nixosModule = self.nixosModules.default;

      devShells = forEachSupportedSystem ({ pkgs }:
        let
          concatMajorMinor = v:
            pkgs.lib.pipe v [
              pkgs.lib.versions.splitVersion
              (pkgs.lib.sublist 0 2)
              pkgs.lib.concatStrings
            ];

          python = pkgs."python${concatMajorMinor pythonVersion}";
          
          pythonWithPackages = python.withPackages (ps: with ps; [
            beautifulsoup4
            requests
            lxml
            markdownify
            tqdm
            python-dotenv
            fake-useragent
            pip
            pyyaml
          ]);
        in
        {
          default = pkgs.mkShell {
            packages = [
              pythonWithPackages
              
              # System dependencies
              pkgs.libxml2
              pkgs.libxslt
              pkgs.zlib
              pkgs.pkg-config
            ];

            shellHook = ''
              export PYTHONPATH=$PYTHONPATH:$(pwd)
              echo "Web downloader development environment ready!"
            '';
          };
        });
    };
}
