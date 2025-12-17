{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python312;
        pythonEnv = python.withPackages (p: [
          # Here goes all the libraries that can't be managed by uv because of dynamic linking issues
          # or that you just want to be managed by nix for one reason or another
          p.numpy
          p.klayout
          p.ruff
          p.pyqt6
          p.py
        ]);
      in
      {
        devShells.default =
          pkgs.mkShell {
            buildInputs = with pkgs; [
              uv
              python
              pythonEnv
              pre-commit
              stdenv.cc.cc.libgcc
            ];

            LD_LIBRARY_PATH = "${
              pkgs.lib.makeLibraryPath (with pkgs; [
                xorg.libX11
              ])
            }:$LD_LIBRARY_PATH";

            nativeBuildInputs = [ pkgs.autoPatchelfHook ];

            shellHook = ''
              pre-commit install
              pre-commit run
              patch=$(autoPatchelf ~/.cache/pre-commit/)
              if [[ $? -ne 0 ]]; then
                echo "$patch"
                exit 1
              else
                echo "patched ~/.cache/pre-commit"
              fi
              rm -rf .venv
              uv venv --python=3.12
              source .venv/bin/activate
              uv pip install -r requirements.txt
              uv pip install -e .
            '';
          };
      }
    );
}
