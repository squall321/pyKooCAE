*KEYWORD
*TITLE
Test_004: Pitching Sweep -40° to +40° - Minimum Model Template
$-------------------------------------------------------------------
$ Hardware Warranty Drop Test
$ Test Case: Pitch 각도 스윕 (-40° ~ +40°, 1° 간격)
$ Purpose: 전후 낙하 각도 민감도 및 디스플레이 각도별 충격 평가
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
