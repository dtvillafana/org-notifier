{
    description = "A basic Python development environment";

    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
        flake-parts.url = "github:hercules-ci/flake-parts";
    };

    outputs = { nixpkgs, flake-utils, ... }:
        flake-utils.lib.eachDefaultSystem (system:
            let
                pkgs = nixpkgs.legacyPackages.${system};
            in
                {
                devShells.default = pkgs.mkShell {
                    buildInputs = with pkgs; [
                        (python312.withPackages(ps: with ps; [
                            (python312Packages.buildPythonPackage {
                                pname = "orgparse";
                                version = "0.1.0";
                                src = pkgs.fetchFromGitHub {
                                    owner = "dtvillafana";
                                    repo = "orgparse";
                                    rev = "master";
                                    sha256 = "sha256-R2IHJ7WUoqH+T/nuhOI8Ek9GKAGib3JSE3FUYDjnv5E=";
                                };
                                pyproject = true;
                                propagatedBuildInputs = with pkgs.python312Packages; [
                                    setuptools
                                    setuptools-scm
                                ];
                                checkInputs = with pkgs.python312Packages; [
                                    pytest
                                    ruff
                                    mypy
                                    lxml
                                ];
                                doCheck = true; # Enable if you have tests
                                meta = with pkgs.lib; {
                                    description = "Emacs org-mode parser in Python";
                                    homepage = "https://github.com/dtvillafana/orgparse";
                                    license = licenses.bsd3;
                                };
                            })
                            requests
                            dateutil
                            pytest
                            shutil
                        ]))
                        python312Packages.black
                        python312Packages.pytest
                    ];
                };
            });
}

