
#include <stdio.h>
#include <stdlib.h>
#include <console.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

#include <id.h>



#include <generated/csr.h>

#include <generated/mem.h>
#include <generated/git.h>


void netboot();
void transmit(int, int);

void readstr(char *s, int size)
{
	static char skip = 0;
	char c[2];
	int ptr;

	c[1] = 0;
	ptr = 0;
	while(1) {
		c[0] = readchar();
		if (c[0] == skip)
			continue;
		skip = 0;
		switch(c[0]) {
			case 0x7f:
			case 0x08:
				if(ptr > 0) {
					ptr--;
					putsnonl("\x08 \x08");
				}
				break;
			case 0x07:
				break;
			case '\r':
				skip = '\n';
				s[ptr] = 0x00;
				putsnonl("\n");
				return;
			case '\n':
				skip = '\r';
				s[ptr] = 0x00;
				putsnonl("\n");
				return;
            case '\e':
                c[0] = readchar();
                switch(c[0]) {
                    case '[':
                        c[0] = readchar();
                        switch(c[0]) {
                            case 'A':
                                if(*s != 0 && ptr == 0){
                                    putsnonl(s);
                                    ptr += strlen(s);
                                }
                                break;
                            default:
                                putsnonl("\e[");
                                putsnonl(c);
                                break;
                        }
                        break;
                }
                break;

			default:
				putsnonl(c);
				s[ptr] = c[0];
				ptr++;
				break;
		}
	}
}



static void ident(void)
{
	char buffer[IDENT_SIZE];

	get_ident(buffer);
	printf("Ident: %s\n", buffer);
}

/* Init + command line */

static void help(void)
{
	puts("LiteX BIOS, available commands:");
	puts("mr         - read address space");
	puts("mw         - write address space");
	puts("mc         - copy address space");
#if (defined CSR_SPIFLASH_BASE && defined SPIFLASH_PAGE_SIZE)
	puts("fe         - erase whole flash");
	puts("fw         - write to flash");

#endif
#ifdef CSR_ETHPHY_MDIO_W_ADDR
	puts("mdiow      - write MDIO register");
	puts("mdior      - read MDIO register");
	puts("mdiod      - dump MDIO registers");
#endif
	puts("");
	puts("crc        - compute CRC32 of a part of the address space");
	puts("ident      - display identifier");
	puts("");
#ifdef CSR_CTRL_BASE
	puts("reboot     - reset processor");
#endif
#ifdef CSR_ETHMAC_BASE
	puts("netboot    - boot via TFTP");
#endif
	puts("serialboot - boot via SFL");
#ifdef FLASH_BOOT_ADDRESS
	puts("flashboot  - boot from flash");
#endif
#ifdef ROM_BOOT_ADDRESS
	puts("romboot    - boot from embedded rom");
#endif
	puts("");
#ifdef CSR_SDRAM_BASE
	puts("memtest    - run a memory test");
#endif
}

static char *get_token(char **str)
{
	char *c, *d;

	c = (char *)strchr(*str, ' ');
	if(c == NULL) {
		d = *str;
		*str = *str+strlen(*str);
		return d;
	}
	*c = 0;
	d = *str;
	*str = c+1;
	return d;
}

#ifdef CSR_CTRL_BASE
static void reboot(void)
{
	ctrl_reset_write(1);
}
#endif

void do_command(char *c)
{
	char *token;

	token = get_token(&c);

	if(strcmp(token, "ident") == 0) ident();
#ifdef CSR_CTRL_BASE
	else if(strcmp(token, "reboot") == 0) reboot();
#endif
	else if(strcmp(token, "") != 0)
		printf("Command not found\n");
}
