public class GenMissingBreakBug045 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
            case 2:
                label = "new";
                break;
            case 3:
                label = "draft";
                break;
            case 4:
                label = "shipped";
                break;
            case 5:
                label = "final";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static int sum2(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }
}
