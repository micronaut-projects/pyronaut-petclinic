package petclinic.views;

import io.micronaut.context.annotation.Prototype;
import io.micronaut.context.python.PooledValue;
import io.micronaut.context.python.PythonContextRuntime;
import io.micronaut.core.io.Writable;
import io.micronaut.views.ViewsRenderer;

@Prototype
public class PythonTemplateViewsRenderer implements ViewsRenderer<Object, Object> {
    private final PooledValue renderView;
    private final PooledValue exists;

    public PythonTemplateViewsRenderer() {
        this.renderView = PythonContextRuntime.withPooledValue("from petclinic.views.renderer import render_view\nrender_view");
        this.exists = PythonContextRuntime.withPooledValue("from petclinic.views.renderer import exists\nexists");
    }

    @Override
    public Writable render(String viewName, Object data, Object request) {
        String html = renderView.executeAsString(viewName, data);
        return writer -> writer.write(html);
    }

    @Override
    public boolean exists(String viewName) {
        return exists.executeAsBoolean(viewName);
    }
}
