public class GenIncorrectConditionalBug075 {
    static int sum1(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }

    static int sum2(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static void printAll3(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static int clamp4(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void announce(int stock) {
        if (stock = 10) {
            System.out.println("hit the target");
        }
    }

    static int drain5(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }
}
