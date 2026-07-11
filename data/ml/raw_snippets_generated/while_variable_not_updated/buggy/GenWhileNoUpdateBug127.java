public class GenWhileNoUpdateBug127 {
    static void pump(boolean open, int count) {
        while (!open) {
            System.out.println(count);
            count++;
        }
    }
}
