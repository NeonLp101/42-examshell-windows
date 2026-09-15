#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

static unsigned int	g_seed;

__attribute__((unused))
static unsigned int	tst_rand(void)
{
	g_seed = g_seed * 1103515245u + 12345u;
	return ((g_seed >> 8) & 0xffffff);
}

__attribute__((unused))
static int	tst_start(int argc, char **argv)
{
	int	t;

	t = (argc > 1) ? atoi(argv[1]) : 0;
	g_seed = (unsigned int)t * 2654435761u + 7u;
	return (t);
}

/* prints a C string literal, with escapes, e.g. "a\tb" */
__attribute__((unused))
static void	tst_put_str(const char *s)
{
	if (!s)
	{
		printf("NULL");
		return ;
	}
	putchar('"');
	for (; *s; s++)
	{
		if (*s == '\t')
			printf("\\t");
		else if (*s == '\n')
			printf("\\n");
		else if (*s == '\v')
			printf("\\v");
		else if (*s == '\f')
			printf("\\f");
		else if (*s == '\r')
			printf("\\r");
		else if (*s == '"' || *s == '\\')
			printf("\\%c", *s);
		else
			putchar(*s);
	}
	putchar('"');
}

/* random string of length 0..maxlen made of charset */
__attribute__((unused))
static char	*tst_rand_str(char *buf, int maxlen, const char *charset)
{
	int		len;
	int		i;
	size_t	n;

	len = (int)(tst_rand() % (unsigned int)(maxlen + 1));
	n = strlen(charset);
	for (i = 0; i < len; i++)
		buf[i] = charset[tst_rand() % n];
	buf[len] = '\0';
	return (buf);
}

__attribute__((unused))
static char	*tst_dup(const char *s)
{
	size_t	len;
	char	*d;

	len = strlen(s);
	d = malloc(len + 1);
	memcpy(d, s, len + 1);
	return (d);
}

int	ft_atoi_base(const char *str, int str_base);

static void	tst(const char *s, int base)
{
	printf("ft_atoi_base(");
	tst_put_str(s);
	printf(", %d) = ", base);
	fflush(stdout);
	printf("%d\n", ft_atoi_base(s, base));
}

int	main(int argc, char **argv)
{
	char	buf[64];
	char	tmp[64];
	int		i;
	int		n;
	int		len;
	int		base;
	int		value;
	int		d;

	if (tst_start(argc, argv) == 0)
	{
		tst("0", 10);
		tst("42", 10);
		tst("-42", 10);
		tst("ff", 16);
		tst("FF", 16);
		tst("-Ff", 16);
		tst("101", 2);
		tst("777", 8);
		tst("12fdb3", 16);
		tst("12FDB3", 16);
		tst("10", 3);
		tst("2147483647", 10);
		tst("7fffffff", 16);
		tst("", 10);
		tst("9a", 10);
		tst("12fdb3", 8);
		tst("18", 8);
		tst("102", 2);
		tst("g1", 16);
		return (0);
	}
	for (i = 0; i < 8; i++)
	{
		base = 2 + (int)(tst_rand() % 15);
		value = (int)(tst_rand() % 1000000);
		len = 0;
		do
		{
			d = value % base;
			tmp[len++] = (tst_rand() % 2) ? "0123456789abcdef"[d] : "0123456789ABCDEF"[d];
			value /= base;
		} while (value);
		n = 0;
		if (tst_rand() % 3 == 0)
			buf[n++] = '-';
		while (len)
			buf[n++] = tmp[--len];
		buf[n] = '\0';
		tst(buf, base);
	}
	return (0);
}
