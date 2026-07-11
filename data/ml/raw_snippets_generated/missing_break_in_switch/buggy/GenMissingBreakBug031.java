public class GenMissingBreakBug031 {
    static String describe1(int stock) {
        if (stock < 10) {
            return "low";
        } else if (stock > 50) {
            return "high";
        }
        return "medium";
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "expired";
                break;
            case 4:
                label = "paid";
            case 5:
                label = "queued";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
