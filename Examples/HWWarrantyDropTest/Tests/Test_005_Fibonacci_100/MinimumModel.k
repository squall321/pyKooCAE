*KEYWORD
*TITLE
Test_005: Fibonacci Lattice 100 Directions - Minimum Model Template
$-------------------------------------------------------------------
$ Hardware Warranty Drop Test
$ Test Case: 100방향 균일분포 (Fibonacci Spiral)
$ Purpose: 전방향 균일 샘플링 및 통계적 낙하 평가
$-------------------------------------------------------------------
*CONTROL_TERMINATION
$#  endtim    endcyc     dtmin    endeng    endmas      nosol
     0.050         0       0.0       0.0       0.0         0
*CONTROL_TIMESTEP
$#  dtinit    tssfac      isdo    tslimt     dt2ms      lctm     erode     ms1st
       0.0       0.9         0       0.0       0.0         0         0         0
*DATABASE_BINARY_D3PLOT
$#      dt      lcdt      beam     npltc    psetid
    0.0005         0         0         0         0
*DATABASE_EXTENT_BINARY
$#   neiph     neips    maxint    strflg    sigflg    epsflg    rltflg    engflg
         0         0         3         1         1         1         1         1
*END
