class VenueInfo:
    def __init__(self, venueName: str, streetAddress: str, addressLocality: str, addressRegion: str, postalCode: int):
        self.addressRegion = addressRegion
        self.venueName = venueName
        self.addressLocality = addressLocality
        self.streetAddress = streetAddress
        self.postalCode = postalCode

    def __str__(self):
        return str(self.__dict__)

