import sys
import socket
import logging
import asyncio


#inline CSDelegate::Packet::Packet(BYTE _type, WORD _key, BYTE num)
#{
#   version = Version;
#   type = _type;
#   packet_num = (num == 0) ? 0xff : num;  // 0xff means request all from mstr svr
#   packet_tot = 0;
#   key = _key;
#   id = 0;
#   data[0] = '\0';
#}
# enum
# {
#    MaxPacketSize = 1500, MaxHeaderSize = 24,
# };
#    struct PingInfo {
#       UInt8 gameType;
#       UInt8 playerCount;
#       UInt8 maxPlayers;
#       int ping;
#       char name[32];
#       char address[256];
#       PingInfo() { ping = Unknown_Ping; }
#    };
#
#    struct GameInfo {
#       int ping;   // valid only if carried from PingEntry to GameEntry
#       WORD key;   // for determining if the response contains additional information
#       char address[256];
#       int dataSize;
#       UInt8 data[DNet::MaxPacketSize - (4*sizeof(BYTE) + 2*sizeof(WORD))]; // ms fix - must be same as Packet::DataSize above
#          //UInt8 data[Packet::DataSize];
#       GameInfo() { address[0] = '\0'; dataSize = 0; ping = Unknown_Ping; }
#    };
#
#    struct PingEntry {
#       enum { General, Enumerated };
#       WORD key;
#       int type;                 // gen or enum
#       int no;                   // for mstr srvr, packet no of n (e.g. 7 of 9)
#       int tries;                // no of attampts to ping, so far
#       UInt32 time;              // time when this entry was sent
#       char address[256];
#       PingEntry(const char *_address, int _no = 0);
#    };
#
#    struct GameEntry {
#       int ping;  // valid only if carried from PingEntry
#       int tries;
#       UInt32 time;
#       char address[256];
#       GameEntry(const char *_address, int _ping = Unknown_Ping);
#    };
#
#       enum GameInfoPacketType
#       {
#          PingInfoQuery          = 0x03,    // aka GAMESPY_QUERY in mstrsvr.h
#          PingInfoResponse       = 0x04,    //  "  GAMESVR_REPLY  "  "
#          MasterServerHeartbeat  = 0x05,    //  "  HEARTBT_MESSAGE
#          MasterServerList       = 0x06,    //  "  MSTRSVR_REPLY
#    		GameInfoQuery          = 0x07,    //  "  GAMESVR_VERIFY
#    		GameInfoResponse       = 0x08,
#       };


class TribesMasterClient:
    def __str__(self):
        return "%s:%s" % (self.ip, self.port)
    def __unicode__(self):
        return "%s:%s" % (self.ip, self.port)
    def __repr__(self):
        return "%s:%s" % (self.ip, self.port)

    def __init__(self, ip, port):
        self.logger = logging.getLogger("tribes_qry")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s".encode())
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.logger.setLevel(logging.INFO)

        self.dataidx = 0
        self.data = None
        self.ip = ip
        self.port = port
        self.maxPlayers = 0
        self.playerCount = 0
        self.teamCount = 0
        self.cpu = 0
        self.motd = b''
        self.modName = b''
        self.version = b''
        self.missionName = b''
        self.serverName = b''
        self.missionType = b''
        self.teamscoreheading= b''
        self.clientscoreheading= b''
        self.gamename = b''
        self.dedicated = False
        self.password = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)
        self.players = []
        self.teams = {}

    def log(self, msg, *args, **kwargs):
        try:
            #print(msg, *args, **kwargs)
            self.logger.info(msg, *args, **kwargs)
        except:
            self.logger.exception()

    def __del__(self):
        if self.sock:
            self.sock.close()

    def readByte(self):
        if self.data is None or self.dataidx+1 >= len(self.data):
             return None
        tmpByte = int.from_bytes(self.data[self.dataidx:self.dataidx+1], byteorder="little", signed=True)
        self.dataidx +=1
        return tmpByte

    def readWord(self):
        if self.data is None or self.dataidx+2 >= len(self.data):
             return None
        tmpByte = int.from_bytes(self.data[self.dataidx:self.dataidx+2], byteorder="little", signed=True)
        self.dataidx +=2
        return tmpByte

    def readStr(self, encoding_str = 'ascii', onerror='ignore'):
        if self.data is None or self.dataidx >= len(self.data):
             return None
        tmpByte = self.readByteStr()
        if tmpByte is None:
            return None
        return tmpByte.decode(encoding_str, onerror)

    def readByteStr(self):
        if self.data is None or self.dataidx >= len(self.data):
             return None
        tmpname = None
        strlength = self.data[self.dataidx]
        if strlength:
            tmpname = (self.data[self.dataidx+1:strlength+self.dataidx+1])
        self.dataidx += 1 + strlength
        return tmpname
        #.decode(encoding_str, onerror) if tmpname and isinstance(tmpname, bytes) and encoding_str and encoding_str != 'b' else "%s" % tmpname

    async def Query(self, readplayerdata=False):
        try:
            data1 = bytearray([0x62, 0x2a, 0x2a])
            self.sock.sendto(data1, (self.ip,self.port))
            self.data, _ = self.sock.recvfrom(4096)

            self.teams = {"-1":("Observer","", -1,[]) }
            self.players = []
            if len(self.data) > 4:
                self.dataidx = 4
                self.gamename = self.readStr()
                self.version =  self.readStr()
                self.serverName =  self.readStr()
                self.dedicated =  self.readByte() == 1
                self.password =  self.readByte() == 1
                self.playerCount =  self.readByte()
                self.maxPlayers =  self.readByte()
                self.cpu =  self.readWord()
                self.modName =  self.readStr()
                self.missionType =  self.readStr()
                self.missionName =  self.readStr()
                self.motd =  self.readStr()
                self.teamCount =  self.readByte()
                self.teamscoreheading=  self.readByteStr()
                self.clientscoreheading=  self.readByteStr()
                if readplayerdata :
                    if self.teamCount:
                        for teamIdx in range( min(8,self.teamCount)):
                            tmp1 = self.readStr()
                            tmp2 = self.readByteStr()
                            self.teams["%s" % teamIdx] = (tmp1,tmp2,teamIdx,[])
                        if self.playerCount:
                            for _ in range(self.playerCount):
                                ping = self.readByte() << 2
                                pl = self.readByte() * 100
                                team = self.readByte()
                                name = self.readStr()
                                score = self.readStr()
                                tmpval = (ping, pl,None, team, name, score)
                                self.players.append(tmpval)
                                teamstr = "%s" % team
                                teamobj = self.teams.get(teamstr)
                                if teamobj:
                                    teamobj[3].append(tmpval)

        except:
            self.logger.exception()

async def discord_get_serverinfo(ip, port):
    tribes_srv = None
    try:
        tribes_srv = TribesMasterClient(ip, port)
        try:
            await tribes_srv.Query(readplayerdata=True)
        except:
            tribes_srv.logger.exception("inner")
    except:
        logging.exception("%s %s" % (ip, port))
    return tribes_srv
