public class GenWhileNoUpdateBug134 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static void pump(boolean active, int count) {
        while (!active) {
            System.out.println(count);
            count++;
        }
    }
}
