public class GenWhileNoUpdateBug111 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int sum2(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static boolean isEven3(int stock) {
        return stock % 2 == 0;
    }

    static void pump(boolean armed, int points) {
        while (!armed) {
            System.out.println(points);
            points++;
        }
    }
}
