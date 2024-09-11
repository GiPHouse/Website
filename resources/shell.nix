with import <nixpkgs> {}; 

mkShell {
 
  shellHook = ''
    export LD_LIBRARY_PATH=${lib.makeLibraryPath [ stdenv.cc.cc ]}
  '';

  buildInputs = [
    gcc-unwrapped
    python310Packages.numpy
    libffi
    python310
    poetry
  ];
}