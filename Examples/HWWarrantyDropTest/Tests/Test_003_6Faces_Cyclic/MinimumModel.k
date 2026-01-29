*KEYWORD
*TITLE
Test_003: 6 Faces Cyclic Drop - Minimum Model Template
$-------------------------------------------------------------------
$ Hardware Warranty Drop Test
$ Test Case: 6면 3회 연속 낙하 (Cyclic 각도 순환)
$ Purpose: 다양한 방향 순차 낙하 및 빠른 연속 낙하 검증
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
