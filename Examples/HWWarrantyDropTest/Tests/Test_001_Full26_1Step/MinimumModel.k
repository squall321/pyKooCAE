*KEYWORD
*TITLE
Test_001: Full 26 Directions Single Drop - Minimum Model Template
$-------------------------------------------------------------------
$ Hardware Warranty Drop Test
$ Test Case: 26방향 1회 낙하 (Face 6 + Edge 12 + Corner 8)
$ Purpose: 전방향 취약점 탐색 및 완전 보증 테스트
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
