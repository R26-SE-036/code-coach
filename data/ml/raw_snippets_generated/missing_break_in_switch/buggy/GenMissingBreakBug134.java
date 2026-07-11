public class GenMissingBreakBug134 {
    static int drain1(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }

    static void printAll2(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }

    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "expired";
            case 3:
                label = "shipped";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
