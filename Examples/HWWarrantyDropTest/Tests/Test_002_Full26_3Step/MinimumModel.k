*KEYWORD
*TITLE
Test_002: Full 26 Directions 3-Step Cumulative Drop - Minimum Model Template
$-------------------------------------------------------------------
$ Hardware Warranty Drop Test
$ Test Case: 26방향 3회 연속 낙하 (동일 각도 반복)
$ Purpose: 반복 낙하 내구성 및 누적 손상 평가
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
