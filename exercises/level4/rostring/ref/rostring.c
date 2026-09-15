#include <unistd.h>

static int	is_blank(char c)
{
	return (c == ' ' || c == '\t');
}

int	main(int argc, char **argv)
{
	char	*s;
	int		i;
	int		first_start;
	int		first_len;
	int		printed;

	if (argc >= 2)
	{
		s = argv[1];
		i = 0;
		while (is_blank(s[i]))
			i++;
		first_start = i;
		while (s[i] && !is_blank(s[i]))
			i++;
		first_len = i - first_start;
		printed = 0;
		while (s[i])
		{
			while (is_blank(s[i]))
				i++;
			if (!s[i])
				break ;
			if (printed)
				write(1, " ", 1);
			while (s[i] && !is_blank(s[i]))
				write(1, &s[i++], 1);
			printed = 1;
		}
		if (printed && first_len)
			write(1, " ", 1);
		write(1, s + first_start, first_len);
	}
	write(1, "\n", 1);
	return (0);
}
