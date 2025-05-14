{ config, lib, pkgs, self, ... }:

with lib;

let
  cfg = config.services.web-downloader;
in {
  options.services.web-downloader = {
    enable = mkEnableOption "web-downloader package";
    
    package = mkOption {
      type = types.package;
      default = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
      defaultText = "web-downloader";
      description = "The web-downloader package to use";
    };
  };
  
  config = mkIf cfg.enable {
    # Add the web-downloader package to the system environment
    environment.systemPackages = [ cfg.package ];
  };
} 