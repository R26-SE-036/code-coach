public class GenCleanGeneric035 {
    static boolean isEven1(int limit) {
        return limit % 2 == 0;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int sum3(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "shipped";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static int largest5(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }
}
