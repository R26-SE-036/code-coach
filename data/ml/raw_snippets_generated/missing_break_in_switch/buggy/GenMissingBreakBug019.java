public class GenMissingBreakBug019 {
    static int largest1(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }

    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "closed";
                break;
            case 3:
                label = "shipped";
            case 4:
                label = "final";
                break;
            case 5:
                label = "expired";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
