ctx.createRectangularRegion('usb_core',64,24,72,44)
usb_core = []

for k,v in ctx.nets:
    if "hyperram_hyperramx2_" in k and "streamablehyperram" not in k:
        usb_core += k
        for u in v.users:
            print(f'Selecting: {k} - {u.cell.name} for usb_core region')
            ctx.constrainCellToRegion(u.cell.name, 'usb_core')


#for k,v in ctx.cells:
#    if "usb_core" in k:
#        print(f'selecting: {k} for usb region')
#        ctx.constrainCellToRegion(k, 'usb')