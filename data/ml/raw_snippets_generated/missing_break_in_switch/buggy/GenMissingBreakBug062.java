public class GenMissingBreakBug062 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain2(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "queued";
            case 3:
                label = "expired";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
