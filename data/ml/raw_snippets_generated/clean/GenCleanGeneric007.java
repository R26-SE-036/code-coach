public class GenCleanGeneric007 {
    static String describe1(int limit) {
        if (limit < 10) {
            return "low";
        } else if (limit > 50) {
            return "high";
        }
        return "medium";
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
