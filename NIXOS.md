# Using web-downloader with NixOS

This guide explains how to use web-downloader as a NixOS package.

## Installation Methods

There are two ways to install web-downloader in NixOS:

### Method 1: Direct Package Installation

The simplest approach - just add it to your packages:

```nix
# In your configuration.nix
{ pkgs, ... }:

{
  # Option 1: Using flakes
  inputs.web-downloader.url = "github:yourusername/web-downloader";
  
  environment.systemPackages = with pkgs; [
    # Add other packages here
    inputs.web-downloader.packages.${system}.default
  ];
}
```

### Method 2: Using the NixOS Module

Or enable the service (just adds it to environment.systemPackages for you)

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    web-downloader.url = "github:yourusername/web-downloader"; # Replace with your repo URL
  };

  outputs = { self, nixpkgs, web-downloader, ... }: {
    nixosConfigurations = {
      your-hostname = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux"; # or your system architecture
        modules = [
          ./configuration.nix
          web-downloader.nixosModules.default
          {
            # Enable the web-downloader package
            services.web-downloader.enable = true;
          }
        ];
      };
    };
  };
}
```

## Command Line Usage

Once installed, use web-downloader by providing a URL:

```bash
web-downloader https://example.com
```

This automatically:
1. Extracts the domain from the URL (example.com)
2. Creates a directory with that domain name in your current location
3. Places all downloaded content in that directory

```bash
# Behind the scenes, it runs:
python main.py https://example.com --output-dir ./example.com
```

### Additional options:

You can pass any other options after the URL:

```bash
web-downloader https://example.com --depth 3 --delay 2.0 --ignore-robots
```

If you want to specify a custom output directory instead of using the domain name:

```bash
web-downloader https://example.com --output-dir /custom/path
```

## Troubleshooting

### Import Errors

If you encounter import errors like:
```
ImportError: attempted relative import with no known parent package
```

This happens when Python can't properly locate the module structure. The fixes:

1. **Use the wrapper script**: Instead of executing Python files directly, use the `web-downloader` command which ensures the proper environment is set up.

2. **Working directory**: If developing or modifying the code, make sure your working directory is structured correctly with the package layout as a Python module.

3. **Nix run usage**: When using `nix run`, remember to separate your options with `--`:
   ```bash
   # CORRECT
   nix run . -- https://example.com
   
   # INCORRECT (will cause errors)
   nix run . https://example.com
   ```

### Permission Issues

If you encounter permission issues when writing files:

1. Make sure you have write permissions in the current directory
2. Try specifying an output directory where you have full permissions:
   ```bash
   web-downloader https://example.com --output-dir ~/Downloads/example-site
   ```

## Building and Testing Locally

To build the package locally:

```bash
nix build
```

To run the package without installing:

```bash
nix run -- https://example.com
```

To enter a development shell:

```bash
nix develop
``` 