#include <stdio.h>
#include <stdlib.h>

int	main(int argc, char **argv)
{
	int		a;
	int		b;
	char	op;

	if (argc == 4)
	{
		a = atoi(argv[1]);
		b = atoi(argv[3]);
		op = argv[2][0];
		if (op == '+')
			printf("%d", a + b);
		else if (op == '-')
			printf("%d", a - b);
		else if (op == '*')
			printf("%d", a * b);
		else if (op == '/')
			printf("%d", a / b);
		else if (op == '%')
			printf("%d", a % b);
	}
	printf("\n");
	return (0);
}
