public class GenMissingBreakFix159 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean isEven3(int attempts) {
        return attempts % 2 == 0;
    }

    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "paid";
                break;
            case 3:
                label = "new";
                break;
            case 4:
                label = "shipped";
                break;
            case 5:
                label = "closed";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
