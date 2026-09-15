#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Same layout as the t_point required by the subject. */
typedef struct s_tst_point
{
	int	x;
	int	y;
}		t_tst_point;

void	flood_fill(char **tab, t_tst_point size, t_tst_point begin);

static unsigned int	g_seed;

static unsigned int	tst_rand(void)
{
	g_seed = g_seed * 1103515245u + 12345u;
	return ((g_seed >> 8) & 0xffffff);
}

static void	tst(const char **zone, int w, int h, int bx, int by)
{
	char		**area;
	t_tst_point	size;
	t_tst_point	begin;
	int			i;

	area = malloc(sizeof(char *) * h);
	for (i = 0; i < h; i++)
	{
		area[i] = malloc(w + 1);
		memcpy(area[i], zone[i], w);
		area[i][w] = '\0';
	}
	printf("size = {%d, %d}, begin = {%d, %d}\n", w, h, bx, by);
	for (i = 0; i < h; i++)
		printf("  %s\n", area[i]);
	printf("after flood_fill:\n");
	fflush(stdout);
	size.x = w;
	size.y = h;
	begin.x = bx;
	begin.y = by;
	flood_fill(area, size, begin);
	for (i = 0; i < h; i++)
		printf("  %s\n", area[i]);
	printf("\n");
}

int	main(int argc, char **argv)
{
	static const char	*subject[] = {"11111111", "10001001", "10010001",
		"10110001", "11100001"};
	static const char	*one[] = {"0"};
	static const char	*row[] = {"00100"};
	static const char	*col[] = {"0", "0", "1", "0"};
	static const char	*diag[] = {"0101", "1010", "0101", "1010"};
	static const char	*spiral[] = {"0000000000", "1111111110", "0000000010",
		"0111111010", "0100000010", "0111111110"};
	static const char	*wide[] = {"abcabcabcabc", "aaaaaaaaaaaa", "cbacbacbacba"};
	static const char	charsets[][4] = {"01", "012", "ab.", "0.."};
	char				rows[20][32];
	const char			*zone[20];
	int					t;
	int					i;
	int					x;
	int					y;
	int					w;
	int					h;
	int					cs;

	t = (argc > 1) ? atoi(argv[1]) : 0;
	if (t == 0)
	{
		tst(subject, 8, 5, 7, 4);
		tst(subject, 8, 5, 0, 0);
		tst(subject, 8, 5, 1, 1);
		tst(one, 1, 1, 0, 0);
		tst(row, 5, 1, 0, 0);
		tst(row, 5, 1, 2, 0);
		tst(col, 1, 4, 0, 3);
		tst(col, 1, 4, 0, 1);
		tst(diag, 4, 4, 1, 1);
		tst(spiral, 10, 6, 0, 0);
		tst(wide, 12, 3, 5, 1);
		return (0);
	}
	g_seed = (unsigned int)t * 2654435761u;
	for (i = 0; i < 3; i++)
	{
		w = 1 + (int)(tst_rand() % 30);
		h = 1 + (int)(tst_rand() % 15);
		cs = (int)(tst_rand() % 4);
		for (y = 0; y < h; y++)
		{
			for (x = 0; x < w; x++)
				rows[y][x] = charsets[cs][tst_rand() % strlen(charsets[cs])];
			rows[y][w] = '\0';
			zone[y] = rows[y];
		}
		tst(zone, w, h, (int)(tst_rand() % w), (int)(tst_rand() % h));
	}
	return (0);
}
