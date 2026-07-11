public class GenWhileNoUpdateBug093 {
    static int sum1(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static boolean isEven2(int stock) {
        return stock % 2 == 0;
    }

    static void printAll3(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static int drain4(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static boolean isEven5(int limit) {
        return limit % 2 == 0;
    }

    static int gather(int limit, int steps) {
        int sum = 0;
        while (limit < steps) {
            sum += limit;
        }
        return sum;
    }
}
