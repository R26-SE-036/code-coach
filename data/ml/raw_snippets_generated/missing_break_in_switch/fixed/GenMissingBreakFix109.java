public class GenMissingBreakFix109 {
    static boolean isEven1(int quota) {
        return quota % 2 == 0;
    }

    static void printAll2(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "draft";
                break;
            case 4:
                label = "queued";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
