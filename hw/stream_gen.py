
from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.interconnect import stream



class StreamGenerator(Module):
    def __init__(self):
        # Wishbone interface
        self.source = source = stream.Endpoint([('data',8)])

        self.submodules.fsm = fsm = FSM()
        

        counter = Signal(32)

        counter_done = Signal()
        counter_ce = Signal()
        counter_val = Signal(32)

        self.sync += [
            If(counter_ce,
                counter.eq(counter_val)
            ).Elif(counter > 0,
                counter.eq(counter - 1)
            )
        ]

        self.comb += [
            counter_done.eq(counter == 0)
        ]

        char = Signal(8, reset=0x40)
        idx = Signal(32)


        data_to_send = bytearray("""
                        \x1b[0m
                                                                 ___                              ____           _     
                                                                / _ \ _ __ __ _ _ __   __ _  ___ / ___|_ __ __ _| |__  
                                                               | | | | '__/ _` | '_ \ / _` |/ _ \ |   | '__/ _` | '_ \ 
                                                               | |_| | | | (_| | | | | (_| |  __/ |___| | | (_| | |_) |
                                                                \___/|_|  \__,_|_| |_|\__, |\___|\____|_|  \__,_|_.__/ 
                                                                                      |___/                            \x1b[1m
                                                               @gregdavill           Buy yours today! groupgets.com/crab
                                                                                                                             
..............```````````````````````````````````````````````..----..``````````````````````````````````````                                                                                                                                   
.................`````````````````````````````````````````.:/+oooo++///:-.``````--.`````````````````````````                                                                                                                                  
.....................```````````````````````````````````.:+osoo++++ooo/+oo+/-..+o/-...`````````````````````` ``                                                                                                                               
.......................````````````````````````````````.+oss/::-----:so/oyyo/s++/:........````````````````````````                                                                                                                            
.............................`````````````````````````:ososs..```````+o/syy-:/-``.-............`  ``````````````````                                                                                                                          
.....................................................:ossoss/.`````.:++oyhh+:`` .---::::-.....`    ```````````````````                                                                                                                        
..................................................../osssssyso+/////+oyyhhh+-.`.:::::::---.:+/-`   ..``````````````````                                                                                                                       
..................................................-+sssosysssssysssosyyhdhss+-.-:-.-::/::---:/+-``.`-.`````````````````````                                                                                                                   
...........................................``.....:syyyyysssssyyys+/::+yysssdyoo+:-//+ooo++/:-:.---` .:::-.````````````````` `                                                                                                                
.......................................... `:/:o:-.-:osyyso++shhho//.``::/s+dmmddy++o++oo+/-:::-::/-.``/ooo+:-.``````````````` `                                                                                                              
.......................................-. .-+/yyhoo-----://+ohhyoyyys/-..:oshymmmmdhdy+/:..-://:::-./++sssso++//:--.```````````````                                                                                                           
...................................----` .-:::::///--::---:+yhooyhhddd:-:yyhysyyhyhdddyhs-``./++:. -+sss++oo/:::o+/o+:-.`````````````                                                                                                         
.................................-----``-:::::::-----:s+//oyoooyhhdddy:ssyhhhhssyyoooyo+/-.../yo:..:+oos/:oo+::/++oo++/+/:::-.`````````                                                                                                       
..............................-------``-::::::::::::-oyooo:+s++syddmdhsyyyhyy+oshysssd:``-/:--:/+:/+oosssoooooo++oo+:--:o/+o+/::-.````````` ``                                                                                                
...........................--------.`.:::::::::::-:///+//-+ssosydddmmmdhhdddddhhys+oyh..:+:-:-+sssy+/+oso++yyoo+o//++//+o+oo+///+://:-.````` ``                                                                                               
........................----------.`.:::::::::-:-..o+/--+shysyhddmmmmmmmmmmdmdmmmmdhds`-/+:ooosssss+/+sso+sso:/oooo+++ooosoo:---//+oo+/:--..````````                                                                                          
.....................-----------:.`:+:os//:::--:---//-:+syooohdddmdmdmmddmddhdmmmmhhys+:-:+sssssssss+oyhyyysoosss/-:+oo+////oo+/+ooo/::/+:/o/:-.````````                                                                                      
.................-------------::////osyyhyo::--:yso+.:+syoyyydhhddmhdddddhhydmmmdddddhyyooooosssssys+yyooyyhdddhs/::+ysyoooooosssyss-.-:+/+oo++//---.```````                                                                                  
..............-------------::::+syysso//+o:----/+ydh++ss+syhhhhhddhhhdhdhyydmmdhhyyddddhyss++ooossysoso+hmmmddddys++yhhhhhhhhyoo+oo++++ooooo---:+/:o+/:-.``````                                                                               
...........--------------::::::/+ossyyyyso+::--.`-so+ss+syssyhhddhydhdhdhdddddhhyshhyyddhyy++shyssooyyodmmmmmmmy+oyyyhdhhhdhdshhys+///+osyoo:-./++oo+///+::/:-.`````                                                                          
........--------------::::::////+++oydhhhhhyo+/:+y/+yo/osssyyyhdmmmddhdhhhhdddhhhdhyoohmmdhysyhysshsshhhdmmmmds/oyssyddyyhhhhdddddyyyysssso/+/+oos++-.--//:oo/::-..````````                                                                   
......--------------::::::////+++ooydmmddhddhhy+hd+ooooshhyhhdmmdddmmmmmdyyhyyhddmhssyymmdhhdhddyydhyhyyhdddh+:/soohdhyyhhyhdddddddddddhysso+oo/oyho+:-/o+oo/://+/-+/:-.```````                                                               
...--------------:::::::////++++ooydmmmmdhdmmmdshdo//osyhhyhhmmdddddmmmmdsshyshhdhhyyyhmmdyhddhdddddhyyyhoyysoosshdddhhhyhhdddddddddddmmmdhyyyyyyys///+o+sso/..-/+/o+///:-...````````                                                         
..-------------:::::::////+++oooshdmmddmmmmmmdhysooossssyyydmmmdddddmmmdhosyyhhdyoysshmmddmdmdyhmddhyyyhhysossyhdddhyhdyyhdddddddddddddmmmmmddhhyyyysssssyyos+:oo++o:-::/+-+o/:-.```````                                                      
--------------::::::////++++oooshdmmmdddddyysyyysosshyhoshddmmmmmddmmmdysssyyddyshyshdmdydmmddmmmdhyyyyyys//+syhhhyyyhhyhddddddhdddddddddddddddddhhhyyysyys+o:+syyyho..-:+/o+////:-:-.````````                                                
------------::::::////++++ooosshddmmmmmddyoyy+oosssyhddyyhdmmdmmmmmmmdsssyyysyyshmdhmmdmmmmdyhmmdhyyyyhhhy+::ohdhhsshhhhddddddddddddhhdddyyyyhhdhhdyshyyyyyyssssssss//+ooo/o:`--:+:/o+/-..```````                                             
-----------::::::////+++ooossyyhhdddddhhhhssos/o/+osyhho+shddddmdmdmdsyy+ydmmmdyymmmmdydmmdmmmmdhyyyyyysossoshdhysyhyyhddddddddhyhdhhhhdysyyshdhhhhyyy+ossyysyhyyso+/+syyyhhs/../+/o+/:/::-:/:-.``````                                        
---------::::::////++++ooossyyyyyyyysyysyyyyyyyy++syhhs+sooso+yhdddhhyhhhdyhdddhhmmmmmdmmdydmmmhyyyyyyyh//:ohhdhyyhyshdhhhhhdhyyyhhyyhhhhhyyhhhhhhhhy//ooosoooosyyhysssossss/:osssoo-..--/::oo/::-..``````                                    
--------::::::////+++oooossyyyyyyhhhyhyyooyyyyyyyyysyddyyossoyhhy+/syyhddmdhhyhhdmNmmmmmmmmmmmmmdhyyss+oosshdddhhyyyhddddddhhhhyhhhyhhhyyhhhhhhhhhhy//oo+ossooooo+oo+oddhyos+ossyyhhys/./+/o/--://:-++:-.`````                                
-------::::::////+++oooosssyyyoyyhhhhhhyyosyyyyyyhysdssossdmmmdho+o-oyoosmmmmdddddmmmmNmmmmmmmmmmhyhhho:-ohddhdhdhyhdddddddhhhyhhyyhdhyyhhhhhhhhhhs:+oosoooooo+oooo/+yhdhhydddhysssso/ssyyyhs/...:/:o+/:::-...````                            
-------::::://///+++ooosssysyy/yyhhhhhhhysoyyyyshhsyyoodmmmdddmmdhoyhhhhhhdmdhhdmmmmmNNNNNNmmmmNmdss//oyyhddddddddddddhhddhhyyhhhhhhhhhhdddddhhhhs:+ooooooo+oosooo/ohhhhhhhhdddhhhyyysssyyy+/o//+ooso:-::/+-/o+/:.```                         
------::::::////+++ooossssysyyosyhhhhhhysoysyyshdyohysmmmmmmmmdyhhdysoyhyyddddddmmmmmmmmmNNNmmmNNmyyo+:ohddddddddddddddddhyhyhhhhddhhhhddddhhhhhs:+oosooooooosooo+yyyyyyyyyhhddhhhhhhhhyyys++:+:sss+++-..-//ossssoo+:-.``                     
-----::::::////+++oooossssyysyyysyyyyysssy+oos/o/s+ydmmmmmmmdyoshdmmdhhyyydmdmmmmmdmmmmmmmmmmmmmddo:/syhdddddddddddddddddhhhhhhhhdhyhhdddhhhhhho:+oosooooo+oooos+yyyysyyyyyyhhhhhhhhhhhhyyyyyysoss/---:/+++/ssssssooooo+:.`                   
-----::::::////+++oooossssyyyysyyyyyyyyyyyyysossosyddhdddmmh+/ssodddhhdhydmmmmmmmdmmmmdyydmmmmddhhs+:+hdddddddddddddddddddddhyyhdyyyddddhdhhhho:+oooooo+oooosoo+yyyyyyysyysyyyhhhhhyyhhhyyhyyyyyssss++/:o+/osso++//:::/+so:`                  
-----::::::////+++oooossssyyyhhhyyyyyyyyyyyyhhhy+yhhyyyyhyhs++yyddhhdddhdmmdmmmmmmmmmdys/+dmmhyyo+shhddmmmmmmdddddddddddddddhhhdhhhddddhhhhhho:oss++sso++oooso+yyyyyyyyyyysyyyhyhhhyyhhhyyyyyyyy+/+sssssssssso/+:-...-::/so-`                 
----::::::////++++oooosssssyyyyyhhhhyyyysyysyhyssyyssyyssyhy+++osyhhdddhmddmNNmmmmmddddyydddmmmds+shhyddmmddmmmmmmdddddddddddddddddddddddhhho/oss+/++/yh+/oss+yyyyyyysyyyyyyhhhhhhhhhhhyyyyyyyyys+:osso+oo+//+:...`````-/oo:``                
----:::::://///+++oooosssssssyyyyyyyhhhhhyyyyyyyyyoohhhyoyyyyyysssshdhhhdmmNNNmmmmdhydddddddmmh+syyhyydmddhhddddmmmmmmmddddddddddddddddddhho/so+o+++++:--+osohyyhyyyyyyyyyyyhhhyyhhhhhhyyyyyyyys+:sss/-++ooo+o:......`.:+oo:```               
----:::::://///+++ooooosssssssyyyyyyyyyyhhhhhhyyyyysyyyyyyyyhhysyyhhysysyhddmmmmmysosydhhmmmmh/oyyyhhdddddhyhhhhddddmmmmmmmddddddddddddddho/syo+/++++://o+:ohhhhyyyyyyyyyyyyyhhhhhhhhhhhhyyyyys//ssyy/++oooosso/:----:+oso/-```               
----:::::::////++++ooooossssssssyyyyyyyyyyyhhhhhhhyyyyyyyysohhhyshhhhhhhyyhddddhsoohsydshhysyoosssyyhddddhhhhhhhyyyhddddddmmmmmdddddhhddho+yyhhso+++:/-+sosyyyhhhyyyyhyyyyyhhhhhhhhhhhhyyyyyys/:ssssy+++oss+oooooooosssso/-``````             
-----:::::://///++++oooooossssssssyyyyyyyyyyyyyhhhhhhhhyyyyyyyyyhhhyhhhyshhdhyo++shhshyyddhhy++syyyhhdddddddhdhhhhhyyyyhhddddmmmmmmmdddy++yyhdddddho-/++oohyyyhhyyyyyyhyyhhhhhhhhhhhhyyyyyyys+/ssysshysoo+++ooo+:/osssso/:.``````             
-----::::::::////+++++oooooossssssssssyyyyyyyyyyyyhhhhhhhhhhyyyhhhysdhhyshhhyyysyyyyyysshdmmdysssoydddhhhhdddhhhhhhhhhyyhddddmmmmmmmmmd+/oyyhddddddy/osooyyyhhyyyyyyyyyyyyhhhhhhhhhhhhhhyyys//syyyyhhhhhyyoo++yyo+ossso/:.```````             
------:::::::://///++++++ooooooossssssssssyyyyyyyyyyyyyhhhhhhhhhhyyhhhyyhhyshhhy+yhyyso+/syyysyyhyhddhhhhhhhhhdhhhhddhhhddhhdddmmmmmdhyososossyyhyyyyyooyyyyhhyyyyyyyyyhhhhhhhhhhhhhhhhhyys//syyyyhhhhhhyo:ooossssssso/:.````````             
-------::::::::///////+++++++ooooooossssssssssyyyyyyyyyyyyhhhhhhhhhhhyyhhyyohhhyoyyysso+oyso/:++hmmddddhhhhhhhdddddddddddhsyhhhhhhyyy+ossssssssosoyyyoohyhhhhhyyyyyhyyyyhhhhhhhhhhhhhhhsss//syyhhddddhhho:/:-+sssssso/:.``````````            
---------:::::::::////////+++++++oooooooossssssssssyyyyyyyyyyyyhhhhhhhhhhyyyyyyyyyy+hhhs/syyso+ydmmmmmmmdddhhhdddddddddhyysosyyysooso+/+ssssssssssssoshhhhhhyyyhyyyyyhhhhhhhhhhhhhhhhhyso//syyyhdddddddho+::/ossssso/:.```````````            
-----------::::::::://////////++++++++oooooooossssssssssyyyyyyyyyyyyhhhhhhhhhyyyyss+yyysossossssydhhddmmNmmmmdddddddddhysosooyyso+os+//+ssssyyysssyoshhhhhhyyyyyyyyyyhhhhhhhhhhhhhhhhhyo//ssssyyhyo+sooshy/:sssssso/:-`````````````           
-------------:::::::::::://////////++++++++oooooooosssssssssyyyyyyyyyyyyyhhhhhhhhyysssssyss/yhhy+shhhhddmmmNNmmmmmdddhyyysyssoosssss+ossosoossyyyyoshhhhhhhyyyyyhyyyyhhhhhhhhhhhhhhhhys//sssssyyyhhyo::oyysossssso/:.``````````````           
----------------:::::::::::::///////////++++++++oooooooossssssssssyyyyyyyyyyyhhhhhhhhyyyyss+oysssyysyyyyshmmmmmmmmmmdyssyys+o+ooossoosyyssoo+/+yyoshhhhhhhhhhhhhyyhhhhhhhhhhhhhhhhhhys//sssooossydddhs+osssssssso/:-.```````````````          
-------------------:::::::::::::::://////////++++++++oooooooossssssssssyyyyyyyyyyyyhhhhhhhyysssyyys/shhyoohhhhhddmhyooysosssssso+oos+oyoshdds+/ooshhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhyys//sss+ossyyyyhyyossssssssso/:-.`````````````````         
------------------------::::::::::::::::///////////++++++++oooooooosssssssssyyyyyyyyyyyyhhhhhhyyyssoosyysyyssyhhssys+oyo:::+yyssssossyso+ossosysshhysyyyhhhhhhhhhhhhhhhhhhhhhhhhhyys//sssosyssssyyysssoos+ossso+:-.```````````````````        
-----------------------------::::::::::::::::///////////++++++++oooooooosssssssssyyyyyyyyyyyyyhhhhyyyssyyyy+ohhys+yyssoo+++syy+/+ossshyosoo+:+osshdhhhyyyyyyhhhhhhhhhhhhhhhhhhhhhys/+ssysydhysoossssoo+so//oso+:-..```````````````````        
----------------------------------::::::::::::::::///////////+++++++++oooooooosssssssssyyyyyyyyyyyhhhhhyyysssyyyssssoyyyo/syys+/:+:+yhyyyhhysoo/-smmmmmdhhhyhhhhhhhhhhhhhhhhhhhhys/+syyyyhhhhhyooyhy+oyo:+oso+:-..````````````````````        
---------------------------------------:::::::::::::::::///////////++++++++oooooooossssssssssyyyyyyyyyyhhhhyyyssysso/yyys+ssssss++osyo:/ohdmmddyoshmmmNNmmmmddhhhhhhhhhyyhhhhhhys/+yyyhhhhhhhhhyosdhssyyssso+/-...`````````````````````       
--------------------------------------------::::::::::::::::::///////////++++++++ooooooossssssssssyyyyyyyyyyhhhhyyssosssssss+yhhy/oyyssooyyhhdhhhhddmmmmhdmmmmmmddhhhhhhhhhhhhys/+yyhhhhhyyyyhhysyyyyoossso+/-...````````````````````````     
--------------------------------------------------::::::::::::::::::://////////+++++++oooooooossssssssssyyyyyyyyyhhhyyyssyoo/oyysossssyssosyhh+/+ooyhdmmddhhmmmdmmmmdddhhhhhyys/oyyhhyydmhyyyhyssyyyo-::+o+/-....`````````````````````````    
""", encoding='cp437')


        #display init data 
        
        out_buffer = self.specials.out_buffer = Memory(8, len(data_to_send), init=data_to_send)
        self.specials.out_buffer_rd = out_buffer_rd = out_buffer.get_port(write_capable=False)
        self.autocsr_exclude = ['out_buffer']

        self.comb += [
            out_buffer_rd.adr.eq(idx),
        ]

        start_reg = Signal()

        fsm.act('INIT',
            counter_val.eq(int(5000e-3 * 65e6)),
            counter_ce.eq(1),

            NextValue(idx,0),
            NextState('ADD_CHAR')
        )


        fsm.act('ADD_CHAR',
            If(counter_done,
                source.data.eq(out_buffer_rd.dat_r),
                source.valid.eq(1),
                If(source.ready,
                    counter_val.eq(int(50e-6 * 65e6)),
                    counter_ce.eq(1),
                    NextValue(idx,idx+1),
                    If(idx > (len(data_to_send)-1),
                        NextState('INIT')
                    )
                ),
            )
        )


        fsm.act('DONE',
           NextState('DONE'),
        )
