public class GenWhileNoUpdateBug040 {
    static int sum1(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static void pump(boolean running, int budget) {
        while (!running) {
            System.out.println(budget);
            budget++;
        }
    }

    static boolean isEven3(int total) {
        return total % 2 == 0;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static int drain5(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }
}
