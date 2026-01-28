from __future__ import annotations
import copy
import os

if __name__ == "__main__":
    from KooSection import KooSectionIGASolid
else:
    from KooCAEManager.KooSection import KooSectionIGASolid


# 디폴트 옵션 (예제 파일 기반)
DEFAULT_OPTIONS = {
    # === 요소 크기 ===
    'element_edge_length': {
        'rr': 0.6,
        'rs': 0.6,
        'rt': 0.6
    },

    # === Integration Rule ===
    'integration_rule': 0,  # 0=reduced Gauss, 1=Full Gauss

    # === Stabilization ===
    'stabilization': {
        'styp': 4,
        'tollg': 1.0e-3
    },

    # === Bounding Box ===
    'auto_bbox': True,
    'bbox_offset_ratio': 1.1,  # 1.0 = 확장 없음, 1.1 = 10% 확장
    'manual_bbox': None,  # {'xmin': ..., 'xmax': ..., ...}

    # === IGA_3D_NURBS_XYZ ===
    'nurbs_params': {
        'nr': 2, 'ns': 2, 'nt': 2,          # knot 개수
        'pr': 1, 'ps': 1, 'pt': 1,          # 다항식 차수
        'unir': 1, 'unis': 1, 'unit': 1     # uniform knot vector
    },

    # === IGA_SOLID ===
    'iga_solid_params': {
        'nisr': 1,
        'niss': 1,
        'nist': 1
    },

    # === IGA_REFINE_SOLID ===
    'refine_params': {
        'rtyp': 2,      # refinement type
        'hrtyp': 2,     # h-refinement type
        'itr': 2,       # r-direction iterations
        'its': 2,       # s-direction iterations
        'itt': 2        # t-direction iterations
    },

    # === IGA_DEV_VOLUME_XYZ ===
    'volume_params': {
        'tetmsh': -1,   # 고정값 (FE embedding)
        'esid': None,   # 비워둠
        'fsid': None    # 비워둠
    },

    # === PART 이름 템플릿 ===
    'part_name_template': 'Nurbs-Solid_{source_name}'
}


class KooIGAPart:
    """IGA 솔리드 파트를 관리하는 클래스"""

    def __init__(self, source_part, pid, mid, secid, options):
        """
        IGA 파트 초기화

        Args:
            source_part: 원본 FEM 파트 (KooPart)
            pid: IGA Part ID (VID, SID, PATCHID, RID와 동일)
            mid: Material ID (MaterialManager가 할당)
            secid: Section ID (SectionManager가 할당)
            options: 사용자 옵션 딕셔너리
        """
        self.source_part = source_part
        self.pid = pid
        self.mid = mid
        self.secid = secid

        # 옵션 병합 (사용자 옵션 + 디폴트)
        self.options = self._MergeWithDefaults(options)

        # 출력 파일 경로
        self.output_file = self.options.get('output_file', f'iga_part_{pid}.k')

        # 파트 이름 생성
        template = self.options.get('part_name_template')
        self.name = template.format(source_name=source_part.name)

        # 바운딩박스 계산
        if self.options['auto_bbox']:
            self.bbox = self.CalculateBoundingBox()
        else:
            self.bbox = self.options['manual_bbox']
            if self.bbox is None:
                raise ValueError("auto_bbox=False이면 manual_bbox를 제공해야 합니다")

        # 요소 크기
        self.element_edge_length = self.options['element_edge_length']

        # Integration rule
        self.integration_rule = self.options['integration_rule']

        # Stabilization
        self.stabilization = self.options['stabilization']

        # NURBS 파라미터
        self.nurbs_params = self.options['nurbs_params']

        # IGA_SOLID 파라미터
        self.iga_solid_params = self.options['iga_solid_params']

        # Refine 파라미터
        self.refine_params = self.options['refine_params']

        # Volume 파라미터
        self.volume_params = self.options['volume_params']

    def _MergeWithDefaults(self, user_options):
        """
        사용자 옵션과 디폴트 값을 병합

        Args:
            user_options: 사용자 제공 옵션

        Returns:
            완전한 옵션 딕셔너리
        """
        merged = copy.deepcopy(DEFAULT_OPTIONS)

        for key, value in user_options.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # 딕셔너리 타입은 재귀 병합
                merged[key].update(value)
            else:
                # 단일 값은 덮어쓰기
                merged[key] = value

        return merged

    def CalculateBoundingBox(self):
        """
        원본 파트의 요소들로부터 바운딩박스 계산

        Returns:
            dict: {'xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax'}
        """
        # 모든 노드 좌표 수집
        all_coords = []

        for elem in self.source_part.elementManager.elements.values():
            for node in elem.nodes:
                all_coords.append([node.x, node.y, node.z])

        if len(all_coords) == 0:
            raise ValueError(f"Part {self.source_part.id}에 노드가 없습니다")

        # min/max 계산
        xs = [coord[0] for coord in all_coords]
        ys = [coord[1] for coord in all_coords]
        zs = [coord[2] for coord in all_coords]

        xmin_raw, xmax_raw = min(xs), max(xs)
        ymin_raw, ymax_raw = min(ys), max(ys)
        zmin_raw, zmax_raw = min(zs), max(zs)

        # bbox 중심 계산
        x_center = (xmin_raw + xmax_raw) / 2.0
        y_center = (ymin_raw + ymax_raw) / 2.0
        z_center = (zmin_raw + zmax_raw) / 2.0

        # bbox 크기 계산
        x_size = xmax_raw - xmin_raw
        y_size = ymax_raw - ymin_raw
        z_size = zmax_raw - zmin_raw

        # 오프셋 비율 적용
        ratio = self.options['bbox_offset_ratio']

        xmin = x_center - (x_size / 2.0) * ratio
        xmax = x_center + (x_size / 2.0) * ratio
        ymin = y_center - (y_size / 2.0) * ratio
        ymax = y_center + (y_size / 2.0) * ratio
        zmin = z_center - (z_size / 2.0) * ratio
        zmax = z_center + (z_size / 2.0) * ratio

        return {
            'xmin': xmin, 'xmax': xmax,
            'ymin': ymin, 'ymax': ymax,
            'zmin': zmin, 'zmax': zmax
        }

    def GenerateIGAKeywords(self):
        """
        IGA 키워드 문자열 생성

        Returns:
            str: 전체 IGA 키워드 블록
        """
        keywords = ""

        # 1. PARAMETER_LOCAL
        keywords += self._GenerateParameterLocal()

        # 2. PARAMETER_EXPRESSION_LOCAL
        keywords += self._GenerateParameterExpressionLocal()

        # 3. IGA_DEV_STABILIZATION
        keywords += self._GenerateIGAStabilization()

        # 4. PART
        keywords += self._GeneratePart()

        # 5. SECTION_IGA_SOLID
        keywords += self._GenerateSectionIGASolid()

        # 6. IGA_DEV_VOLUME_XYZ
        keywords += self._GenerateIGADevVolumeXYZ()

        # 7. IGA_SOLID
        keywords += self._GenerateIGASolid()

        # 8. IGA_3D_NURBS_XYZ
        keywords += self._GenerateIGA3DNurbsXYZ()

        # 9. IGA_REFINE_SOLID
        keywords += self._GenerateIGARefineSolid()

        return keywords

    def _GenerateParameterLocal(self):
        """*PARAMETER_LOCAL 생성"""
        s = "*PARAMETER_LOCAL\n"
        s += "$    PRMR1      VAL1\n"
        s += "$ 1. Unique input file ID\n"
        s += f"Iid           {self.pid:5d}\n"
        s += "$ 2. Material ID\n"
        s += f"Imid          {self.mid:5d}\n"
        s += "$ 3. FE Solid PID\n"
        s += f"Ifepid        {self.source_part.id:5d}\n"
        s += "$ 4. Box corner points\n"
        s += f"Rxmin     {self.bbox['xmin']:10.3e}\n"
        s += f"Rxmax     {self.bbox['xmax']:10.3e}\n"
        s += f"Rymin     {self.bbox['ymin']:10.3e}\n"
        s += f"Rymax     {self.bbox['ymax']:10.3e}\n"
        s += f"Rzmin     {self.bbox['zmin']:10.3e}\n"
        s += f"Rzmax     {self.bbox['zmax']:10.3e}\n"
        s += "$ 5. Element edge length\n"
        s += f"Rrr       {self.element_edge_length['rr']:10.3e}\n"
        s += f"Rrs       {self.element_edge_length['rs']:10.3e}\n"
        s += f"Rrt       {self.element_edge_length['rt']:10.3e}\n"
        s += "$ 6. Integration rule\n"
        s += f"Iir           {self.integration_rule:5d}\n"
        s += "$ 7. Stabilization\n"
        s += f"Istyp         {self.stabilization['styp']:5d}\n"
        s += f"Rtollg    {self.stabilization['tollg']:10.3e}\n"
        return s

    def _GenerateParameterExpressionLocal(self):
        """*PARAMETER_EXPRESSION_LOCAL 생성"""
        s = "*PARAMETER_EXPRESSION_LOCAL\n"
        s += "rxminn, &xmin-&rr\n"
        s += "rxmaxx, &xmax+&rr\n"
        s += "ryminn, &ymin-&rs\n"
        s += "rymaxx, &ymax+&rs\n"
        s += "rzminn, &zmin-&rt\n"
        s += "rzmaxx, &zmax+&rt\n"
        return s

    def _GenerateIGAStabilization(self):
        """*IGA_DEV_STABILIZATION 생성"""
        s = "*IGA_DEV_STABILIZATION\n"
        s += "$      sid      styp                                   tollg\n"
        s += f"       &id     &styp                                  &tollg\n"
        return s

    def _GeneratePart(self):
        """*PART 생성"""
        s = "*PART\n"
        s += "$#\n"
        s += f"{self.name}\n"
        s += "$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid\n"
        s += f"       &id       &id      &mid\n"
        return s

    def _GenerateSectionIGASolid(self):
        """*SECTION_IGA_SOLID 생성"""
        s = "*SECTION_IGA_SOLID\n"
        s += "$#   secid    elform        ir\n"
        s += f"       &id         0       &ir\n"
        return s

    def _GenerateIGADevVolumeXYZ(self):
        """*IGA_DEV_VOLUME_XYZ 생성"""
        s = "*IGA_DEV_VOLUME_XYZ\n"
        s += "$#     vid   patchid       pid      esid      fsid    TETMSH      MYTP\n"
        s += f"       &id       &id                                      {self.volume_params['tetmsh']:2d}\n"
        s += "$#     PID of existing FEA solid with tetmesh\n"
        s += f"    &fepid\n"
        s += "$#   brid1     brid2     brid3     brid4     brid5     brid6     brid7     brid8\n"
        s += "\n"
        return s

    def _GenerateIGASolid(self):
        """*IGA_SOLID 생성"""
        s = "*IGA_SOLID\n"
        s += "$#     sid       pid      nisr      niss      nist       rid\n"
        nisr = self.iga_solid_params['nisr']
        niss = self.iga_solid_params['niss']
        nist = self.iga_solid_params['nist']
        s += f"       &id       &id    {nisr:6d}    {niss:6d}    {nist:6d}       &id\n"
        return s

    def _GenerateIGA3DNurbsXYZ(self):
        """*IGA_3D_NURBS_XYZ 생성"""
        np = self.nurbs_params
        s = "*IGA_3D_NURBS_XYZ\n"
        s += "$# patchid        nr        ns        nt        pr        ps        pt\n"
        s += f"       &id    {np['nr']:6d}    {np['ns']:6d}    {np['nt']:6d}    {np['pr']:6d}    {np['ps']:6d}    {np['pt']:6d}\n"
        s += "$#    unir      unis      unit\n"
        s += f"    {np['unir']:6d}    {np['unis']:6d}    {np['unit']:6d}\n"
        s += "$#            rfirst               rlast\n"
        s += "              &xminn              &xmaxx\n"
        s += "$#            sfirst               slast\n"
        s += "              &yminn              &ymaxx\n"
        s += "$#            tfirst               tlast\n"
        s += "              &zminn              &zmaxx\n"
        s += "$#                 x                   y                   z                 wgt\n"

        # 8개 제어점 (박스 코너)
        s += "              &xminn              &yminn              &zminn                 1.0\n"
        s += "              &xmaxx              &yminn              &zminn                 1.0\n"
        s += "              &xminn              &ymaxx              &zminn                 1.0\n"
        s += "              &xmaxx              &ymaxx              &zminn                 1.0\n"
        s += "              &xminn              &yminn              &zmaxx                 1.0\n"
        s += "              &xmaxx              &yminn              &zmaxx                 1.0\n"
        s += "              &xminn              &ymaxx              &zmaxx                 1.0\n"
        s += "              &xmaxx              &ymaxx              &zmaxx                 1.0\n"

        return s

    def _GenerateIGARefineSolid(self):
        """*IGA_REFINE_SOLID 생성"""
        rp = self.refine_params
        s = "*IGA_REFINE_SOLID\n"
        s += "$      rid      rtyp\n"
        s += f"       &id    {rp['rtyp']:6d}\n"
        s += "$    hrtyp        rr        rs        rt\n"
        s += f"    {rp['hrtyp']:6d}       &rr       &rs       &rt\n"
        s += "$      itr       its       itt\n"
        s += f"    {rp['itr']:6d}    {rp['its']:6d}    {rp['itt']:6d}\n"
        return s

    def WriteToFile(self):
        """
        IGA 키워드를 별도 파일로 출력

        Returns:
            str: 생성된 파일 경로
        """
        with open(self.output_file, 'w') as f:
            f.write('*KEYWORD\n')
            f.write(self.GenerateIGAKeywords())
            f.write('*END\n')

        return self.output_file

    def WriteStreamIGAKeyword(self, stream):
        """
        Stream에 IGA 키워드 출력 (파일 객체)

        Args:
            stream: 파일 객체 (open()으로 열린 파일)
        """
        stream.write(self.GenerateIGAKeywords())

    def GenerateInclude(self, relative_path=True):
        """
        메인 모델에 삽입할 *INCLUDE 문 생성

        Args:
            relative_path: True면 상대경로, False면 절대경로

        Returns:
            str: "*INCLUDE\nfilename\n"
        """
        if relative_path:
            filename = os.path.basename(self.output_file)
        else:
            filename = os.path.abspath(self.output_file)

        return f"*INCLUDE\n{filename}\n"


if __name__ == "__main__":
    # 간단한 테스트
    print("KooIGAPart module loaded successfully")
    print(f"Default options: {DEFAULT_OPTIONS}")
