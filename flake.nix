{
    description = "A basic Python development environment";

    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
        # flake-parts.url = "github:hercules-ci/flake-parts";
        nixos-generators = {
            url = "github:nix-community/nixos-generators";
            inputs.nixpkgs.follows = "nixpkgs";
        };
    };

    outputs = { self, nixpkgs, flake-utils, nixos-generators, ... }:
        flake-utils.lib.eachDefaultSystem (system:
            let
                pkgs = nixpkgs.legacyPackages.${system};
                python-env = pkgs.python312.withPackages(ps: with ps; [
                    (pkgs.python312Packages.buildPythonPackage {
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
                ]);
                notifier-pkgs = with pkgs; [
                    python-env
                    # pkgs for manual debug
                    file
                    tree
                    # misc must haves
                    neovim
                    git
                    curl
                    wget
                ];
                env-vars = {
                    NTFY_URL  = builtins.getEnv "NTFY_URL";
                };
                git-url-path = "dtvillafana/org-notifier.git"; # WARNING: replace this with your own
                git-url = "github.com"; # WARNING: replace this with your own
            in
                {
                packages = {
                    docker = nixos-generators.nixosGenerate {
                        system = "x86_64-linux";
                        format = "docker";
                        modules = [
                            {
                                config = {
                                    # Open necessary firewall ports (e.g., for SSH access to clone repositories)
                                    networking = {
                                        hostName = "nixos-org-notifier"; # Define your hostname.
                                        # Disable DHCP on this interface
                                        useDHCP = true;
                                        firewall.allowedTCPPorts = [ 22 ];
                                    };

                                    environment = {
                                        variables = env-vars;
                                        etc."org-notifier/service-vars" = {
                                            # Source path is relative to the Nix store
                                            text = ''NTFY_URL="${env-vars.NTFY_URL}"
ORG_BASEDIR="/home/master/git-repos/orgfiles"'';
                                            # Set appropriate permissions
                                            mode = "0600";
                                            user = "master";
                                            group = "master";
                                        };
                                        etc."main.py" = {
                                            # Source path is relative to the Nix store
                                            source = ./src/main.py;
                                            # Set appropriate permissions
                                            mode = "0755";
                                            user = "master";
                                            group = "master";
                                        };
                                        # Ensure the SSH public and private keys are present on the system
                                        etc."ssh/nix-org-notifier" = {
                                            # Source path is relative to the Nix store
                                            source = ./ssh-keys/nix-org-notifier;
                                            # Set appropriate permissions
                                            mode = "0600";
                                            user = "master";
                                            group = "master";
                                        };
                                        etc."ssh/nix-org-notifier.pub" = {
                                            source = ./ssh-keys/nix-org-notifier.pub;
                                            mode = "0644";
                                            user = "master";
                                            group = "master";
                                        };
                                        # List packages installed in system profile. To search, run:
                                        # $ nix search wget
                                        systemPackages = with pkgs; [
                                            neovim
                                            wget
                                            git
                                            curl
                                        ];
                                    };

                                    programs = {
                                        ssh = {
                                            # Configure the specific host connection
                                            extraConfig = ''Host gitlab
HostName ${git-url}
IdentityFile /etc/ssh/nix-org-notifier
User git
                                            '';
                                        };
                                        git = {
                                            enable = true;
                                            config = {
                                                user = {
                                                    name = "nixos-org-notifier-vm";
                                                    email = "person@proton.me";
                                                };
                                            };
                                        };
                                    };

                                    # Ensure the the git-repos directory is present on the system
                                    systemd.tmpfiles.rules = [
                                        "d /home/master/git-repos 0755 master master -"
                                    ];

                                    system.userActivationScripts.cloneGitRepo = {
                                        deps = [];
                                        text = ''
                                            ${pkgs.git}/bin/git clone -c core.sshCommand='${pkgs.openssh}/bin/ssh -o StrictHostKeyChecking=no' gitlab:${git-url-path} /home/master/git-repos/orgfiles
                                        '';
                                    };

                                    systemd.services = {
                                        org-notifier = {
                                            description = "Run org-notifier script";
                                            after = [ "network.target" ];
                                            path = ["/run/current-system/sw"] ++ notifier-pkgs;
                                            serviceConfig = {
                                                Type = "oneshot";
                                                User = "master";
                                                EnvironmentFile = [
                                                    "/etc/org-notifier/service-vars"
                                                ];
                                                ExecStart = "${python-env}/bin/python3 /etc/main.py";
                                            };
                                        };
                                        git-puller = {
                                            description = "Pull git repository";
                                            serviceConfig = {
                                                Type = "oneshot";
                                                User = "master";
                                                WorkingDirectory = "/home/master/git-repos/orgfiles";  # Set this to your repo path
                                                ExecStart = "${pkgs.git}/bin/git pull";
                                            };
                                        };
                                    };

                                    systemd.timers = {
                                        org-notifier = {
                                            description = "Timer for notification script";
                                            wantedBy = [ "timers.target" ];
                                            timerConfig = {
                                                OnCalendar = "minutely";
                                                Persistent = true;  # Run immediately if we missed the last trigger
                                                Unit = "org-notifier.service";
                                            };
                                        };
                                        git-puller = {
                                            description = "Timer for git pull";
                                            wantedBy = [ "timers.target" ];
                                            timerConfig = {
                                                OnCalendar = "*:*:30";  # Runs at 30 seconds past every minute
                                                Persistent = true;
                                                Unit = "git-puller.service";
                                            };
                                        };

                                    };

                                    # Enable the OpenSSH daemon.
                                    services.openssh.enable = true;
                                    users.users.master = {
                                        isNormalUser = true;
                                        extraGroups = [ "wheel" ]; # Enable ‘sudo’ for the user.
                                        packages = with pkgs; [
                                            tree
                                            neovim
                                            git
                                            curl
                                            wget
                                        ];
                                        password = "changeme"; # WARNING: replace with your own
                                    };

                                    security.sudo = {
                                        enable = true;
                                        wheelNeedsPassword = false;
                                    };
                                    system.stateVersion = "nixos-unstable"; # Did you read the comment?
                                    services.chrony.enable = true;
                                    boot.isContainer = true;
                                };
                            }
                        ];
                        specialArgs = {
                            # additional arguments to pass to modules
                            self = self;
                            nixpkgs = nixpkgs;
                        };
                    };
                };
                devShells.default = pkgs.mkShell {
                    buildInputs = with pkgs; [
                        python-env
                        python312Packages.black
                        python312Packages.pytest
                    ];
                };
            });
}
