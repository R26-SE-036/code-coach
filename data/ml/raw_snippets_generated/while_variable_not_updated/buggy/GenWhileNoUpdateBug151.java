public class GenWhileNoUpdateBug151 {
    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int gather(int steps, int budget) {
        int sum = 0;
        while (steps < budget) {
            sum += steps;
        }
        return sum;
    }

    static boolean isEven4(int attempts) {
        return attempts % 2 == 0;
    }

    static int largest5(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }
}
