public class GenWhileNoUpdateBug052 {
    static void countdown(int quota) {
        while (quota > 0) {
            System.out.println("left: " + quota);
        }
    }

    static int drain1(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }
}
