class AanvragenViewDefinition(ViewDefinition):
    def __init__(self):
        mst = MilestoneTableDefinition()
        avt = AanvraagTableDefinition()
        ft  = FilesTableDefinition()
        super().__init__('VIEW_AANVRAGEN', 
                         column_names=['id','datum','stud_id', 'bedrijf_id', 'source_file_id', 'titel','kans','status','beoordeling','datum_str'],
                         key = 'id', join_expression = 
                         SQEjoin(tables=[mst.name, avt.name, ft.name], on_keys=[mst.key, avt.key, 'aanvraag_id'], alias=['M', 'A', 'F']),
                         where=SQE('F.filetype', Ops.EQ, int(File.Type.AANVRAAG_PDF)),
                         columns=['M.id','datum','stud_id', 'bedrijf_id', 'F.ID', 'titel','kans','status','beoordeling','datum_str'])                                 

class VerslagenViewDefinition(ViewDefinition):
    def __init__(self):
        mst = MilestoneTableDefinition()
        vvt = VerslagTableDefinition()
        super().__init__('VIEW_VERSLAGEN', 
                         column_names=['id','datum','stud_id', 'bedrijf_id', 'titel','kans','status','beoordeling','cijfer', 'directory'],
                         key = 'id', join_expression = SQEjoin(tables=[mst.name, vvt.name], on_keys=[mst.key, vvt.key], alias=['M', 'V']),
                         columns=['M.id','datum','stud_id', 'bedrijf_id', 'titel','kans','status','beoordeling','cijfer', 'directory'])
