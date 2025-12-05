{
  description = "A stripped down fork of ledger-autosync";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake {inherit inputs;} {
      systems = import inputs.systems;
      perSystem = {pkgs, ...}: let
        dependencies = with pkgs.python3.pkgs; [ledger] ++ [pkgs.ledger];
        # devDeps = with pkgs.python3Packages; [pandas pandas-stubs xlrd tqdm];
      in {
        packages.default = pkgs.python3Packages.buildPythonApplication {
          pname = "ledger-jester";
          version = "0-unstable";
          pyproject = true;
          src = ./.;
          build-system = with pkgs.python3.pkgs; [setuptools];
          inherit dependencies;
          dontCheckRuntimeDeps = true;
        };
      };
    };
}
