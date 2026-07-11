public class GenCleanStackedLabels014 {
    static String describe1(int attempts) {
        if (attempts < 10) {
            return "low";
        } else if (attempts > 50) {
            return "high";
        }
        return "medium";
    }

    static int drain2(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "final";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static int largest3(int[] values) {
        int best = values[0];
        for (int i = 1; i < values.length; i++) {
            if (values[i] > best) {
                best = values[i];
            }
        }
        return best;
    }

    static void printAll4(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static int clamp5(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void printAll6(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static int drain7(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }
}
