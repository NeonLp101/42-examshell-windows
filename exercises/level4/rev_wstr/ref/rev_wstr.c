#include <unistd.h>

static int	is_blank(char c)
{
	return (c == ' ' || c == '\t');
}

int	main(int argc, char **argv)
{
	char	*s;
	int		i;
	int		end;
	int		printed;

	if (argc == 2)
	{
		s = argv[1];
		i = 0;
		while (s[i])
			i++;
		printed = 0;
		while (--i >= 0)
		{
			if (is_blank(s[i]))
				continue ;
			end = i;
			while (i > 0 && !is_blank(s[i - 1]))
				i--;
			if (printed)
				write(1, " ", 1);
			write(1, s + i, end - i + 1);
			printed = 1;
		}
	}
	write(1, "\n", 1);
	return (0);
}
