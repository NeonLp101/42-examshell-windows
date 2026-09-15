#include <stdio.h>
#include <stdlib.h>

int	main(int argc, char **argv)
{
	long long	n;
	long long	d;
	int			first;

	if (argc == 2)
	{
		n = atoi(argv[1]);
		d = 2;
		first = 1;
		if (n == 1)
			printf("1");
		while (n > 1)
		{
			if (d * d > n)
				d = n;
			if (n % d == 0)
			{
				if (!first)
					printf("*");
				printf("%lld", d);
				first = 0;
				n /= d;
			}
			else
				d++;
		}
	}
	printf("\n");
	return (0);
}
