public class GenOffByOneFix146 {
    static int sum1(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static int sum4(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static int[] duplicate(int[] values) {
        int[] copy = new int[values.length];
        for (int i = 0; i < values.length; i++) {
            copy[i] = values[i];
        }
        return copy;
    }

    static int clamp5(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String status6(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
