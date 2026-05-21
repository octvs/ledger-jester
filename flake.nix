{
  description = "A stripped down fork of ledger-autosync";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake {inherit inputs;} {
      imports = [inputs.treefmt-nix.flakeModule];
      systems = import inputs.systems;
      perSystem = {pkgs, ...}: {
        packages.default = pkgs.python3Packages.buildPythonApplication rec {
          pname = "ledger-jester";
          version = "0-unstable";
          pyproject = true;
          src = ./.;
          build-system = with pkgs.python3.pkgs; [setuptools];
          dependencies = [pkgs.ledger] ++ optional-dependencies.parsers;
          optional-dependencies.parsers = with pkgs.python3.pkgs; [
            pandas
            xlrd
          ];
          dontCheckRuntimeDeps = true;
        };
        treefmt = {
          projectRootFile = "flake.nix";
          programs.alejandra.enable = true;
          programs.ruff-format = {
            enable = true;
            lineLength = 79;
          };
        };
      };
    };
}
