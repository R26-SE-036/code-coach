public class GenMissingBreakFix122 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain2(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "paid";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}
