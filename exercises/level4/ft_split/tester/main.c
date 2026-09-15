#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char	**ft_split(char *str);

static unsigned int	g_seed;

static unsigned int	tst_rand(void)
{
	g_seed = g_seed * 1103515245u + 12345u;
	return ((g_seed >> 8) & 0xffffff);
}

static void	tst_put_escaped(const char *s)
{
	for (; *s; s++)
	{
		if (*s == '\t')
			printf("\\t");
		else if (*s == '\n')
			printf("\\n");
		else if (*s == '"' || *s == '\\')
			printf("\\%c", *s);
		else
			putchar(*s);
	}
}

static void	tst(const char *src)
{
	char	*copy;
	char	**res;
	size_t	len;
	int		i;

	len = strlen(src);
	copy = malloc(len + 1);
	memcpy(copy, src, len + 1);
	printf("ft_split(\"");
	tst_put_escaped(src);
	printf("\") = ");
	fflush(stdout);
	res = ft_split(copy);
	if (!res)
	{
		printf("NULL\n");
		return ;
	}
	printf("{");
	for (i = 0; res[i] && i < 1000; i++)
	{
		printf("\"");
		tst_put_escaped(res[i]);
		printf("\", ");
		fflush(stdout);
	}
	printf("%s}\n", res[i] ? "...no NULL terminator found" : "NULL");
	if (strcmp(copy, src) != 0)
		printf("  !! ft_split modified its input string\n");
}

int	main(int argc, char **argv)
{
	static const char	*fixed[] = {"", " ", "\t\n  \n\t", "hello",
		"hello world", "  hello   world  ", "a b c d e",
		"\tone\ttwo\n\nthree   ", "Que la      lumiere soit et la lumiere fut",
		"no-separators-at-all!", "x", " x ", "multiple\n\nnew\nlines",
		"  ,;:!?  42  ", "tabs\tand spaces \t mixed\t\t", "\n\nz"};
	static const char	charset[] = "abcdefghijklmnopqrstuvwxyzABCXYZ0123456789,.!?-_*";
	char				buf[128];
	int					t;
	int					i;
	int					j;
	int					len;
	unsigned int		r;

	t = (argc > 1) ? atoi(argv[1]) : 0;
	if (t == 0)
	{
		for (i = 0; i < (int)(sizeof(fixed) / sizeof(*fixed)); i++)
			tst(fixed[i]);
		return (0);
	}
	g_seed = (unsigned int)t * 2654435761u;
	for (i = 0; i < 6; i++)
	{
		len = (int)(tst_rand() % 60);
		for (j = 0; j < len; j++)
		{
			r = tst_rand() % 100;
			if (r < 20)
				buf[j] = ' ';
			else if (r < 27)
				buf[j] = '\t';
			else if (r < 32)
				buf[j] = '\n';
			else
				buf[j] = charset[tst_rand() % (sizeof(charset) - 1)];
		}
		buf[len] = '\0';
		tst(buf);
	}
	return (0);
}
