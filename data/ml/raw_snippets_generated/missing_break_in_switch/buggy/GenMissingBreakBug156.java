public class GenMissingBreakBug156 {
    static int sum1(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
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

    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "queued";
            case 3:
                label = "archived";
                break;
            case 4:
                label = "active";
                break;
            case 5:
                label = "final";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static int sum3(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }
}
