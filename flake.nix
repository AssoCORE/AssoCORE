{
  description = "Modular Full-Stack Flake: Flutter, Next.js, Python (uv), and Git Hooks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    android-nixpkgs.url = "github:tadfisher/android-nixpkgs";
    git-hooks = {
      url = "github:cachix/git-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    android-nixpkgs,
    git-hooks,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnfree = true;
            android_sdk.accept_license = true;
          };
        };
        lib = pkgs.lib;

        android-base-packages = sdkPkgs:
          with sdkPkgs; [
            cmdline-tools-latest
            build-tools-34-0-0
            build-tools-35-0-0
            platform-tools
            platforms-android-34
            platforms-android-35
            platforms-android-36
            ndk-28-2-13676358
            cmake-3-22-1
          ];

        androidsdk = android-nixpkgs.sdk.${system} android-base-packages;

        androidsdk-emulator = android-nixpkgs.sdk.${system} (
          sdkPkgs:
            (android-base-packages sdkPkgs)
            ++ [
              sdkPkgs.emulator
              sdkPkgs.system-images-android-34-google-apis-x86-64
            ]
        );

        pre-commit-check = git-hooks.lib.${system}.run {
          src = ./.;
          hooks = {
            biome = {
              enable = true;
              name = "biome hook";
              entry = ''
                ${lib.getExe pkgs.biome} format --write ./front --config-path ${./biome.json}
              '';
            };
            black = {
              enable = true;
              name = "black hook";
              entry = ''
                ${lib.getExe pkgs.black} --quiet ./back
              '';
            };
            convco = {
              enable = true;
              name = "convco hook";
            };
            isort = {
              enable = true;
              name = "isort hook";
              entry = ''
                ${lib.getExe pkgs.isort} ./back
              '';
            };
            alejandra = {
              enable = true;
              name = "alejandra hook";
            };
          };
        };
      in {
        # Define standard Nix formatter (`nix fmt`)
        formatter = pkgs.alejandra;

        checks = {
          inherit pre-commit-check;
        };

        devShells = {
          base = pkgs.mkShell {
            packages = with pkgs; [
              # Frontend / Mobile
              nodejs_20
              pnpm
              jdk17
              gradle
              flutter

              # Backend / Python
              python311
              uv

              # Hook Dependencies
              biome
              black
              isort
              convco
              alejandra

              # Git
              git-lfs
            ];

            env = {
              JAVA_HOME = "${pkgs.jdk17.home}";
            };

            # Combine pre-commit installation
            shellHook = pre-commit-check.shellHook;
            # + ''
            #   echo "developer guidance goes here"
            # '';
          };

          # DEFAULT: Base + Standard Android SDK (No emulator)
          default = pkgs.mkShell {
            inputsFrom = [self.devShells.${system}.base];

            packages = [androidsdk];

            env = {
              ANDROID_HOME = "${androidsdk}/share/android-sdk";
              ANDROID_SDK_ROOT = "${androidsdk}/share/android-sdk";
            };
          };

          # WITH-EMULATOR: Heavy shell with Emulator and Android Studio
          with-emulator = pkgs.mkShell {
            inputsFrom = [self.devShells.${system}.base];

            packages = [
              androidsdk-emulator
              pkgs.android-studio
              pkgs.lsof
              pkgs.chromium
            ];

            env = {
              ANDROID_HOME = "${androidsdk-emulator}/share/android-sdk";
              ANDROID_SDK_ROOT = "${androidsdk-emulator}/share/android-sdk";
              CAPACITOR_ANDROID_STUDIO_PATH = "${lib.getExe pkgs.android-studio}";
            };
          };
        };
      }
    );
}
