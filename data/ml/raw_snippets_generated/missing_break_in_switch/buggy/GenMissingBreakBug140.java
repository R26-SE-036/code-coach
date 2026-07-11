public class GenMissingBreakBug140 {
    static boolean isEven1(int level) {
        return level % 2 == 0;
    }

    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "queued";
                break;
            case 4:
                label = "paid";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static void printAll2(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static int sum3(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static int sum4(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }
}
