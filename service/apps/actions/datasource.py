class Datasource:
    ACT = 'act'
    LGT = 'lgt'
    ARC = 'arc'
    INFOREMO = 'inforemo'

    class ARCVersions:
        V1 = 'v1'
        V2 = 'v2'

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in [cls.ACT, cls.ARC, cls.LGT, cls.INFOREMO]
