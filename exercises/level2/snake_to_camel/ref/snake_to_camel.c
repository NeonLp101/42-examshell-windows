#include <unistd.h>

int	main(int argc, char **argv)
{
	char	*s;
	char	c;

	if (argc == 2)
	{
		s = argv[1];
		while (*s)
		{
			if (*s == '_' && s[1] >= 'a' && s[1] <= 'z')
			{
				s++;
				c = *s - 32;
				write(1, &c, 1);
			}
			else
				write(1, s, 1);
			s++;
		}
	}
	write(1, "\n", 1);
	return (0);
}
